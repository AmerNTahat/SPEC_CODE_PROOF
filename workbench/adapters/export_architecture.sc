// #Sireum
import org.sireum._
import org.sireum.message.Reporter
import org.sireum.cli.HAMR

if (Os.cliArgs.size != 2) {
  eprintln("Usage: export_architecture.sc SOURCE_ROOT OUTPUT_DIRECTORY")
  Os.exit(2)
}
val source = Os.path(Os.cliArgs(0))
val output = Os.path(Os.cliArgs(1))
val reporter = Reporter.create
val options = Cli.SireumHamrSysmlTipeOption("", ISZ(), ISZ(), ISZ(source.value), F)
HAMR.sysmlRun(options, reporter) match {
  case Either.Left((hierarchy, models, inputs, store, hasError)) =>
    if (hasError || reporter.hasError || models.isEmpty) {
      eprintln("INSPECTA_ARCHITECTURE_REJECTED")
      Os.exit(1)
    }
    output.mkdirAll()
    var index: Z = 0
    for (model <- models) {
      (output / s"model-$index.json").writeOver(org.sireum.hamr.ir.JSON.fromAadl(model.model, F))
      index = index + 1
    }
    var declarations: ISZ[String] = ISZ()
    var declarationIndex: Z = 0
    for (entry <- hierarchy.typeMap.entries) {
      entry._2 match {
        case p: org.sireum.hamr.sysml.symbol.TypeInfo.Package =>
          val name = st"${(entry._1, "::")}".render
          (output / s"declaration-$declarationIndex.json").writeOver(org.sireum.hamr.ir.JSON.fromSysmlAstPackage(p.ast, F))
          declarations = declarations :+ s"$declarationIndex\t$name"
          declarationIndex = declarationIndex + 1
        case _ =>
      }
    }
    (output / "declarations.tsv").writeOver(st"${(declarations, "\n")}".render)
    println(s"INSPECTA_ARCHITECTURE_EXPORTED:$index")
  case Either.Right(code) =>
    eprintln(s"INSPECTA_ARCHITECTURE_REJECTED:$code")
    Os.exit(1)
}
